<?php

namespace App\Http\Controllers;

use App\Models\Driver;
use Illuminate\Http\Request;
use App\Jobs\ValidateDriverCredentials;
use Illuminate\Support\Facades\Redis;

class DriverController extends Controller
{
    public function profile($id)
{
    $driver = Driver::with([
        'drugTestResults',
        'violations',
        'feedback',
        'credentials',
        'infractions'
    ])->find($id);

    if (!$driver) {
        return response()->json(['error' => 'Driver not found'], 404);
    }

    ValidateDriverCredentials::dispatch($driver->id);

    return response()->json($driver);
}

    public function showProfile($id)
    {
        $driver = Driver::find($id);

        if (!$driver) {
            return response()->json(['error' => 'Driver not found'], 404);
        }

        return response()->json($driver);
    }

    public function updateProfile(Request $request, $id)
    {
        $driver = Driver::find($id);

        if (!$driver) {
            return response()->json(['error' => 'Driver not found'], 404);
        }

        $validatedData = $request->validate([
            'name' => 'string|max:255',
            'email' => 'email|nullable',
            'phone' => 'string|max:20|nullable',
        ]);

        $driver->update($validatedData);

        return response()->json([
            'message' => 'Profile updated successfully',
            'driver' => $driver
        ]);
    }
}
