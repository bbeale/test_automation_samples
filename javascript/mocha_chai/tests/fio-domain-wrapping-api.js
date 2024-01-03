const hre = require("hardhat");
const ethers = hre.ethers;
require("@nomiclabs/hardhat-ethers");
require("mocha");
const {expect} = require("chai");
const {FIOSDK} = require('@fioprotocol/fiosdk');
const config = require('../config.js');
const {
  newUser,
  fetchJson,
  existingUser,
  callFioApi,
  callFioApiSigned,
  getAccountFromKey,
  randStr
} = require("../utils.js");
const {
  getOracleRecords,
  registerNewBp,
  registerNewOracle,
  setTestOracleFees,
  setupFIONFTcontract,
  registerFioNftOracles,
  cleanUpOraclessTable,
  calculateOracleFeeFromOraclessTable
} = require("./Helpers/wrapping");
let faucet;

before(async function () {
  faucet = new FIOSDK(config.FAUCET_PRIV_KEY, config.FAUCET_PUB_KEY, config.BASE_URL, fetchJson)
});

after(async function () {
  try{
    console.log("          cleaning up...");
    const fAcct = await getAccountFromKey(faucet.publicKey);
    const oracleRecords = await getOracleRecords();
    for (let row in oracleRecords.rows) {
      row = oracleRecords.rows[row]
      // hardcode the exclusion of default bp accounts
      if (row.actor === 'qbxn5zhw2ypw' || row.actor === 'hfdg2qumuvlc' || row.actor === 'wttywsmdmfew')
        continue
      let result = await callFioApiSigned('push_transaction', {
        action: 'unregoracle',
        account: 'fio.oracle',
        actor: fAcct,
        privKey: faucet.privateKey,
        data: {
          oracle_actor: row.actor,
          actor: fAcct
        }
      });
      //console.log("deleted: ", row, result);
    }
  } catch (err){
    throw err;
  }
});





/**
 * A much abridged FIO domain wrap and unwrap sequence
 *
 * Full version can be found in https://github.com/fioprotocol/fio.test/tree/master/tests/fio-domain-wrapping-api.js
 */





describe(`Wrap and unwrap a FIO domain`, function () {

  let oracle1, oracle2, oracle3,
      user1, user2, user3, user4, user5, user6, user7, user8,
      custodians, factory, owner,
      OBT_ID, ORACLE_FEE, WRAP_FEE;

  let fioNft = {
    address: '0xpolygonaddress' + randStr(20)
  };

  before(async function () {
    // test users
    oracle1 = await existingUser('qbxn5zhw2ypw', '5KQ6f9ZgUtagD3LZ4wcMKhhvK9qy4BuwL3L1pkm6E2v62HCne2R', 'FIO7jVQXMNLzSncm7kxwg9gk7XUBYQeJPk8b6QfaK5NVNkh3QZrRr', 'dapixdev', 'bp1@dapixdev');
    user1 = await newUser(faucet);
    user2 = await newUser(faucet);
    user3 = await newUser(faucet);
    user4 = await newUser(faucet);
    user5 = await newUser(faucet);
    user6 = await newUser(faucet);
    user7 = await newUser(faucet);
    user8 = await newUser(faucet);
    newOracle1 = await newUser(faucet);
    oracle2 = await newUser(faucet);
    oracle3 = await newUser(faucet);

    // register new oracles as bps
    await registerNewBp(newOracle1);
    await registerNewBp(oracle2);
    await registerNewBp(oracle3);

    // await newOracles
    await registerNewOracle(newOracle1);
    await registerNewOracle(oracle2);
    await registerNewOracle(oracle3);

    // set oracle fees
    //await setTestOracleFees(oracle1, 11000000000, 11000000000);
    await setTestOracleFees(newOracle1, 11000000000, 11000000000);
    await setTestOracleFees(oracle2, 11000000000, 11000000000);
    await setTestOracleFees(oracle3, 11000000000, 11000000000);

    await faucet.genericAction('transferTokens', {
      payeeFioPublicKey: user1.publicKey,
      amount: 10000000000000,
      maxFee: config.api.transfer_tokens_pub_key.fee,
      technologyProviderId: ''
    });
  });

  it(`query the oracless table, expects the three original new records`, async function () {
    try {
      let origOracles = [];
      const oracleRecords = await getOracleRecords();
      for (let row in oracleRecords.rows) {
        row = oracleRecords.rows[row]
        if (row.actor === 'qbxn5zhw2ypw' || row.actor === 'hfdg2qumuvlc' || row.actor === 'wttywsmdmfew') {
          expect(row).to.have.all.keys('actor', 'fees');
          origOracles.push(row);
        }
      }
      expect(origOracles.length).to.equal(0);
    } catch (err) {
      throw err;
    }
  });

  it(`get the oracle fee from the API`, async function () {
    let result = await callFioApi('get_oracle_fees', {});

    if (result.oracle_fees[0].fee_name === 'wrap_fio_domain')
      ORACLE_FEE = result.oracle_fees[0].fee_amount;
    else
      ORACLE_FEE = result.oracle_fees[1].fee_amount;
    let median_fee = await calculateOracleFeeFromOraclessTable('domain');
    expect(ORACLE_FEE).to.equal(median_fee);
  });

  it(`get wrap fee`, async function () {
    let result = await callFioApi('get_fee', {
      end_point: "wrap_fio_domain",
      fio_address: oracle1.address //"vote1@dapixdev"
    });
    WRAP_FEE = result.fee;
  });

  it(`try to wrap a FIO domain, expect OK`, async function () {
    let domain = user1.domain;
    try {
      const result = await callFioApiSigned('push_transaction', {
        action: 'wrapdomain',
        account: 'fio.oracle',
        actor: user1.account,
        privKey: user1.privateKey,
        data: {
          fio_domain: domain,
          chain_code: "ETH",
          public_address: fioNft.address,
          max_oracle_fee: ORACLE_FEE,
          max_fee: config.maxFee,
          tpid: "",
          actor: user1.account
        }
      });
      expect(result).to.have.any.keys('transaction_id');
      expect(result).to.have.any.keys('processed');
      expect(result.processed.receipt.status).to.equal('executed');
      expect(result.processed.action_traces[0].act.data.fio_domain).to.equal(domain);
      expect(result.processed.action_traces[0].act.data.public_address).to.equal(fioNft.address);
      expect(result.processed.action_traces[0].receipt.response).to.equal(`{"status": "OK","oracle_fee_collected":"${ORACLE_FEE}","fee_collected":${WRAP_FEE}}`);
    } catch (err) {
      throw err;
    }
  });

  // need three oracles to approve unwrap
  it(`first oracle: try to unwrap a FIO domain, expect OK`, async function () {
    try {
      const result = await callFioApiSigned('push_transaction', {
        action: 'unwrapdomain',
        account: 'fio.oracle',
        actor: oracle1.account,
        privKey: oracle1.privateKey,
        data: {
          fio_domain: user1.domain,
          obt_id: OBT_ID,
          fio_address: user1.address,
          actor: oracle1.account
        }
      });
      expect(result).to.have.any.keys('transaction_id');
      expect(result).to.have.any.keys('processed');
    } catch (err) {
      throw err;
    }
  });

  it(`second oracle: try to unwrap a FIO domain, expect OK`, async function () {
    try {
      const result = await callFioApiSigned('push_transaction', {
        action: 'unwrapdomain',
        account: 'fio.oracle',
        actor: oracle2.account,
        privKey: oracle2.privateKey,
        data: {
          fio_domain: user1.domain,
          obt_id: OBT_ID,
          fio_address: user1.address,
          actor: oracle2.account
        }
      });
      expect(result).to.have.any.keys('transaction_id');
      expect(result).to.have.any.keys('processed');
    } catch (err) {
      throw err;
    }
  });

  it(`third oracle: try to unwrap a FIO domain, expect OK`, async function () {
    try {
      const result = await callFioApiSigned('push_transaction', {
        action: 'unwrapdomain',
        account: 'fio.oracle',
        actor: oracle3.account,
        privKey: oracle3.privateKey,
        data: {
          fio_domain: user1.domain,
          obt_id: OBT_ID,
          fio_address: user1.address,
          actor: oracle3.account
        }
      });
      expect(result).to.have.any.keys('transaction_id');
      expect(result).to.have.any.keys('processed');
    } catch (err) {
      throw err;
    }
  });

  // unhappy tests
  it(`(actor and domain owner mismatch) try to wrap a FIO domain`, async function () {
    let domain = user1.domain;
    try {
      const result = await callFioApiSigned('push_transaction', {
        action: 'wrapdomain',
        account: 'fio.oracle',
        actor: newOracle1.account,
        privKey: newOracle1.privateKey,
        data: {
          fio_domain: domain,
          chain_code: "ETH",
          public_address: fioNft.address,
          max_oracle_fee: ORACLE_FEE,
          max_fee: config.maxFee,
          tpid: "",
          actor: newOracle1.account
        }
      });
      expect(result.fields[0].name).to.equal('fio_domain');
      expect(result.fields[0].value).to.equal(domain);
      expect(result.fields[0].error).to.equal('Actor and domain owner mismatch.');
    } catch (err) {
      throw err;
    }
  });

  it(`(empty chain_code) try to wrap a FIO domain`, async function () {
    let domain = user2.domain;
    try {
      const result = await callFioApiSigned('push_transaction', {
        action: 'wrapdomain',
        account: 'fio.oracle',
        actor: user2.account,
        privKey: user2.privateKey,
        data: {
          fio_domain: domain,
          chain_code: "",
          public_address: fioNft.address,
          max_oracle_fee: ORACLE_FEE,
          max_fee: config.maxFee,
          tpid: "",
          actor: user2.account
        }
      });
      expect(result.fields[0].name).to.equal('chain_code');
      expect(result.fields[0].value).to.equal('');
      expect(result.fields[0].error).to.equal('Invalid chain code format');
    } catch (err) {
      throw err;
    }
  });

  it(`(missing chain_code) try to wrap a FIO domain`, async function () {
    let domain = user2.domain;
    try {
      const result = await callFioApiSigned('push_transaction', {
        action: 'wrapdomain',
        account: 'fio.oracle',
        actor: user2.account,
        privKey: user2.privateKey,
        data: {
          fio_domain: domain,
          public_address: fioNft.address,
          max_oracle_fee: ORACLE_FEE,
          max_fee: config.maxFee,
          tpid: "",
          actor: user2.account
        }
      });
      expect(result).to.have.any.keys('transaction_id');
      expect(result).to.have.any.keys('processed');
    } catch (err) {
      expect(err.message).to.equal('missing wrapdomain.chain_code (type=string)');
    }
  });
});
