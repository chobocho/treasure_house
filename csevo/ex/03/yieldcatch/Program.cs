// 슬라이드 p3-v2-yield-catch — catch 가 있는 try 안의 yield, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static IEnumerable<int> Safe()
    {
        try
        {
            yield return 1;
        }
        catch (Exception)
        {
        }
    }

    static IEnumerable<int> Last()
    {
        try { yield return 1; }
        finally { yield return 2; }
    }

    static void Main() { }
}
