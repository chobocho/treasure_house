// 슬라이드 p3-v2-anon-yield — 익명 메서드는 반복기가 될 수 없다, C# 2.0
using System;
using System.Collections;

delegate IEnumerable Source();

class App
{
    static void Main()
    {
        Source s = delegate
        {
            yield return 1;
        };
    }
}
