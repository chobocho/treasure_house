// 슬라이드 p14-v13-ru-mod — unsafe 반복기의 서명과 몸체, C# 13.0
using System;
using System.Collections.Generic;

class App
{
    // C# 13: the modifier is allowed; it covers the signature only
    static unsafe IEnumerable<int> Count(int*[] ptrs)
    {
#if BODY
        int first = *ptrs[0];          // the body is a safe context
#endif
        yield return ptrs.Length;
    }

    static unsafe void Main()
    {
        int a = 1, b = 2;
        foreach (int n in Count(new[] { &a, &b })) Console.WriteLine(n);
    }
}
