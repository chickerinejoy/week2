<?php

namespace App\Jobs;

use App\Models\Driver;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Redis;

class ValidateDriverCredentials implements ShouldQueue
{
        use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    protected $driverId;

    public function __construct($driverId)
    {
        $this->driverId = $driverId;
    }

    public function handle()
    {
        $driver = Driver::find($this->driverId);

        if (!$driver) return;

        // Do your actual credential validation logic here.
        // For example, loop through credentials and check expiry
        foreach ($driver->credentials as $credential) {
            if ($credential->isExpired()) {
                // Maybe log or update DB
            }
        }

        // You could also dispatch events, send notifications, etc.
    }
}
