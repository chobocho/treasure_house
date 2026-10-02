// 슬라이드 p8-v7-locfn-static8 — static 지역 함수, C# 8.0
using System;

class App
{
    static void Main()
    {
        int k = 10;
        Console.WriteLine(Add(1, k));

        static int Add(int x, int y) => x + y;  // captures nothing
#if BAD
        static int Bad(int x) => x + k;         // tries to capture k
#endif
    }
}
