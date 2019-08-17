<?php
use Codeception\Actor;
use Codeception\Exception\ModuleException;
use Codeception\Lib\Friend;


/**
 * Inherited Methods
 * @method void wantToTest($text)
 * @method void wantTo($text)
 * @method void execute($callable)
 * @method void expectTo($prediction)
 * @method void expect($prediction)
 * @method void amGoingTo($argumentation)
 * @method void am($role)
 * @method void lookForwardTo($achieveValue)
 * @method void comment($description)
 * @method Friend haveFriend($name, $actorClass = NULL)
 *
 * @SuppressWarnings(PHPMD)
*/
class ApiTester extends \Codeception\Actor
{
    use _generated\ApiTesterActions;

    /**
     * @param string $endpoint
     * @param array $data
     * @throws ModuleException
     */
    public function callApi($endpoint, $data)
    {
        $this->sendPostRequest($endpoint, $data);
    }
}
