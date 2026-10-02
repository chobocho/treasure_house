// 슬라이드 p10-v9-pat-exh — 범위로 따지는 빠짐없음, C# 9.0
using System;

class App
{
    static string Sign(int x) => x switch
    {
        < 0 => "negative",
#if !BAD
        0 => "zero",
#endif
        > 0 => "positive",
    };

    // the proposal's example: every byte value is handled
    static int Bucket(byte b) =>
        b switch { < 100 => 0, 100 => 1, 101 => 2, > 101 => 3 };

#if GAP
    static string Temp(double t) =>
        t switch { < 10.0 => "cold", > 10.0 => "warm" };
#endif

    static void Main()
    {
        Console.WriteLine(Sign(-4) + " " + Sign(0) + " " + Sign(9));
        Console.WriteLine($"{Bucket(0)} {Bucket(101)} {Bucket(255)}");
    }
}
