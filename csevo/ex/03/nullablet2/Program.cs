// 슬라이드 p3-v2-nullable-generic — 제약 없는 Nullable<T>, C# 2.0
using System;

class App
{
#if Q
    static T? Maybe<T>(T x)
#else
    static Nullable<T> Maybe<T>(T x)
#endif
    {
        return x;
    }

    static void Main()
    {
        Console.WriteLine(Maybe(5).HasValue);
    }
}
