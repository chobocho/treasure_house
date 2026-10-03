// 슬라이드 p11-v10-defassign — 개선된 확정 대입, C# 10.0
using System;

class C
{
    public bool M(out object obj)
    {
        obj = "set";
        return true;
    }
}

class App
{
    static void Main()
    {
        C c = new C();
        if ((c != null && c.M(out object o1)) == true)
            Console.WriteLine("== true    " + o1);
        if ((c != null && c.M(out object o2)) is true)
            Console.WriteLine("is true    " + o2);
        if (c?.M(out object o3) == true)
            Console.WriteLine("?. == true " + o3);
        if (c?.M(out object o4) ?? false)
            Console.WriteLine("?. ?? false " + o4);
        if (c != null ? c.M(out object o5) : false)
            Console.WriteLine("?: false   " + o5);
#if BAD
        if (c?.M(out object o6) != false)    // true also when c is null
            Console.WriteLine(o6);
        if (c?.M(out object o7) == false) { }
        else
            Console.WriteLine(o7);           // c may be null here
#endif
    }
}
