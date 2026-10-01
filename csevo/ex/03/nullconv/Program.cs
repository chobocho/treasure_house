// 슬라이드 p3-v2-nullable-conv — int? 에서 int 로는 캐스트로만, C# 2.0
using System;

class App
{
    static void Main()
    {
        int? a = 3;                       // int -> int?: implicit
        int b = a;                        // int? -> int: needs a cast
        int c = a + 1;                    // the sum is an int?, too
        Console.WriteLine(b + c);
    }
}
