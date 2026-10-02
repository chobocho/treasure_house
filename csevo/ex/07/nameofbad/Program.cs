// 슬라이드 p7-v6-nameof-bad — nameof 가 받지 않는 것, C# 6.0
using System;
using System.Collections.Generic;

class App
{
    static void M<T>() { }

    static void Main()
    {
        string a = "a", b = "b";
        Console.WriteLine(nameof(List<>));       // unbound generic
        Console.WriteLine(nameof(M<int>));       // method type args
        Console.WriteLine(nameof(a.ToString())); // an invocation
        Console.WriteLine(nameof(a + b));        // an expression
        Console.WriteLine(nameof(dynamic));
#if INT
        Console.WriteLine(nameof(int));          // keyword type
#endif
    }
}
