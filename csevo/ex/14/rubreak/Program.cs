// 슬라이드 p14-v13-ru-break — 반복기는 안전 문맥, C# 13.0
using System;
using System.Collections.Generic;

unsafe class C                         // unsafe context
{
    public IEnumerable<int> M()        // an iterator
    {
        yield return 1;
        yield return local();
#if OLD
        int local()                    // fine up to C# 12
#else
        unsafe int local()             // the workaround
#endif
        {
            int x = 2;
            int* p = &x;               // unsafe code
            return *p;
        }
    }
}

class App
{
    static void Main()
    {
        foreach (int v in new C().M()) Console.WriteLine(v);
    }
}
