<?php
namespace Helper;
use Codeception\Exception\ModuleException;
use Codeception\Module;

/**
 * Class Api
 * The "base" of the API testing component
 *
 * Methods: sendGetRequest(endpoint, inputs)
 *              - endpoint: URL string
 *              - inputs: assoc. array of input data
 *
 *          sendPostRequest(endpoint, inputs)
 *              - endpoint: URL string
 *              - inputs: assoc. array of input data
 *
 *          loadDataFixture(directory, filename)
 *              - directory string (within apiFixtures directory, unless _common is specified)
 *              - file name string of the data fixture
 */
class Api extends Module
{
    /**
     * @param string $endpoint
     * @param array $inputs
     * @throws ModuleException
     */
    public function sendGetRequest($endpoint, $inputs)
    {
        /** @var Module\REST $rest */
        $rest = $this->getModule("REST");
        $rest->sendGET($endpoint, $inputs);
    }

    /**
     * @param string $endpoint
     * @param array $inputs
     * @throws ModuleException
     */
    public function sendPostRequest($endpoint, $inputs)
    {
        /** @var Module\REST $rest */
        $rest = $this->getModule("REST");
        $rest->sendPOST($endpoint, $inputs);
    }

    /**
     * @param string fileName
     * @param string directory
     * @return array|bool
     * @throws ModuleException
     */
    public static function loadDataFixture($directory, $fileName)
    {
        $base = sprintf("%s/../../../tests", __DIR__);
        if (strpos($directory, "_common") || $directory === "_common")
            $filePath = realpath(sprintf("%s/_common/dataFixtures/%s.php", $base, $fileName));
        else
            $filePath = realpath(sprintf("%s/dataFixtures/%s/%s.php", $base, $directory, $fileName));
        return is_array(include $filePath) ? include $filePath : false;
    }
}
