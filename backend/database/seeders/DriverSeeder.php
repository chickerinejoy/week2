<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class DriverSeeder extends Seeder
{
    public function run()
    {
        DB::table('drivers')->insert([
            'name' => 'Test Driver',
            'license_number' => 'ABC12345',
            'birthdate' => '1990-01-01', // Required date
            'contact' => '09171234567', // Required string
            'created_at' => now(),
            'updated_at' => now(),
        ]);
    }
}
