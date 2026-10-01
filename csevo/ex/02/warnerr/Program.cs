// 슬라이드 p2-v1-warnerr — #warning 과 #error, C# 1.0
using System;

#warning The retry policy below is a stub.
#if SHIP
#error SHIP builds need a real retry policy.
#endif

class App
{
    static int Retries() { return 0; }

    static void Main()
    {
        Console.WriteLine("retries: " + Retries());
    }
}
