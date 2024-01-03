<?php
namespace users;
use ApiTester;
use Codeception\Exception\ModuleException;


/**
 * @property int timestamp
 * @property int userID
 */
class UserLookupCest
{
    public function _before()
    {
        $this->timestamp = time();
    }

    public function _after()
    {
        $this->userID = null;
    }

    /**
     * @param ApiTester $I
     */
    protected function hasUserInDatabaseToTestWith(ApiTester $I)
    {
        $_ = $I->loadDataFixture("_common", "user");
        $this->userID = $I->haveTestUserInDb($_)["userID"];
    }

    // tests

    /**
     * @param ApiTester $I
     * @throws ModuleException
     */
    public function usersLookupSuccess(ApiTester $I)
    {
        UserLookupCest::hasUserInDatabaseToTestWith($I);
        $data = ["userID" => $this->userID];
        $I->callApi("users/userLookup", $data);
        $I->seeResponseCodeIsSuccessful();
        $I->seeResponseMatchesJsonType([
            "userID"        => "string:regex(~$this->userID~)",
            "lastname"      => "string",
            "firstname"     => "string",
            "email"         => "string:regex(~\@~)",
            "access"        => "boolean",
        ]);
    }

    /**
     * @param ApiTester $I
     * @throws ModuleException
     */
    public function usersLookupFail(ApiTester $I)
    {
        UserLookupCest::hasUserInDatabaseToTestWith($I);
        $data = ["userID" => "pickle"];
        $I->callApi("users/userLookup", $data);
        $I->seeResponseCodeIsClientError();
        $I->seeResponseMatchesJsonType(["error" => "string"]);
    }
}
