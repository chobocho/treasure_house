// 슬라이드 p11-v10-small-misc — 패턴 안의 null! 금지, C# 10.0
using System;

class App
{
    static string Test(object o)
    {
#if OLD
        if (o is null!) return "null (null!)";
#endif
        if (o is null) return "null";
        return "not null";
    }

    static void Main()
    {
        Console.WriteLine(Test(null));
        Console.WriteLine(Test(1));
    }
}
