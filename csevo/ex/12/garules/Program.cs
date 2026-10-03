// 슬라이드 p12-v11-genattr-rules — 형식 인수로 못 오는 것, C# 11.0
using System;
using System.Collections.Generic;

[AttributeUsage(AttributeTargets.All, AllowMultiple = true)]
class AAttribute<T> : Attribute
{
    public override string ToString() => typeof(T).ToString();
}

class Box<T2>
{
#if OPEN
    [A<T2>] void M() { }
#endif
#if NESTED
    [A<List<T2>>] void N() { }
#endif
}

[A<object>, A<ValueTuple<int, int>>, A<nint>, A<int?>]
#if DYN
[A<dynamic>]
#endif
#if NULLABLE
#nullable enable
[A<string?>]
#endif
#if TUPLE
[A<(int X, int Y)>]
#endif
class App
{
    static void Main()
    {
        foreach (object a in typeof(App).GetCustomAttributes(false))
            Console.WriteLine(a);
    }
}
