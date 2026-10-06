// 슬라이드 p14-v13-ru-unsafe — 반복기 안의 unsafe 블록, C# 13.0
using System;
using System.Collections.Generic;

class App
{
    static IEnumerable<int> Doubled(int[] data)
    {
        for (int i = 0; i < data.Length; i++)
        {
            int v;
            unsafe
            {
                fixed (int* p = data) { v = p[i] * 2; }
#if YIELD
                yield return v;           // yield inside unsafe
#elif ADDR
                int* q = &i;              // address of a local
#endif
            }
            yield return v;               // outside: fine
        }
    }

    static void Main()
    {
        Console.WriteLine(string.Join(",", Doubled(new[] { 1, 2, 3 })));
    }
}
