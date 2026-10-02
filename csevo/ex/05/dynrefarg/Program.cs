// 슬라이드 p5-v4-dyn-refarg — ref 매개변수에 dynamic 인자, C# 4.0
using System;

class Program
{
    static void Bump(ref dynamic a) { a = a + 1; }

    static void Main()
    {
        dynamic d = 41;
        Bump(ref d);
        Console.WriteLine(d);
#if BAD
        Bump(d);          // ref is missing
#endif
    }
}
