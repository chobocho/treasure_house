// 슬라이드 p3-v2-yield-type — 반환 형식이 정하는 yield 형식, C# 2.0
using System.Collections;
using System.Collections.Generic;

class App
{
    static IEnumerable Old()              // yield type: object
    {
        yield return 1;
        yield return "two";               // anything goes
    }

    static IEnumerable<int> Typed()       // yield type: int
    {
        yield return 1;
        yield return "two";
    }

    static void Main() { }
}
