// 슬라이드 p3-v2-invariance — List<T> 는 불변, C# 2.0
using System.Collections.Generic;

class App
{
    static void Main()
    {
        List<string> ls = new List<string>();
        List<object> lo = ls;             // no conversion
        lo.Add(42);                       // (this is why)
    }
}
