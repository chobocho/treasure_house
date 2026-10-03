// 슬라이드 p12-v11-math-pattern — T 와 숫자 상수 패턴, C# 11.0
using System;
using System.Numerics;

class App
{
    static bool IsOne<T>(T t) where T : INumberBase<T> =>
#if BAD
        t is 1;                          // would test "is int 1"
#else
        t == T.One;
#endif

    // The pattern still works on a plain object: a type test first
    static bool BoxedOne(object o) => o is 1;

    static void Main()
    {
        Console.WriteLine(IsOne(1.0) + " " + IsOne(1) + " "
            + IsOne(1m));
        Console.WriteLine(BoxedOne(1.0) + " " + BoxedOne(1));
    }
}
