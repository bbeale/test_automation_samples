<?php
namespace Helper;
use Codeception\Exception\ModuleException;
use Codeception\Module;

/**
 * Class DataManager
 *
 * A class for adding records to the database vis a vis $this->getModule("Db")->haveInDatabse()
 * This saves (for the most part) the trouble of manually deleting test data after a test run
 *
 * @package Helper
 * @param string $testing_clerkshipID
 * @param string $testing_programID
 */
class DataManager extends Module
{
    public function haveTestUserInDb($data)
    {
        /** @var Module\Db $db */
        $db = $this->getModule("Db");

        // methods to interact with individual tables as needed to create the application entity
        $id_1 = $db->haveInDatabase("table_1", $data["table_1_data"]);
        $id_2 = $db->haveInDatabase("table_2", $data["table_2_data"]);
        return ["id_1" => $id_1, "id_2" => $id_2];
    }
}
