// 슬라이드 p3-v2-yield-rules — 반복기가 될 수 없는 메서드, C# 2.0
using System.Collections.Generic;

class App
{
    static IEnumerable<int> ByRef(ref int x)
    {
        yield return x;
    }

    static int NotASequence()
    {
        yield return 1;
    }

    static IEnumerable<int> Mixed()
    {
        yield return 1;
        return null;
    }

    static void Main() { }
}
