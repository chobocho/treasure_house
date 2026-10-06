// 슬라이드 p13-v12-brk-dynref — dynamic 인수와 ref 매개변수, C# 12.0
using System;
using Microsoft.CSharp.RuntimeBinder;

class C
{
    public void F(ref dynamic a) { Console.WriteLine("F " + a); }

    public void M(dynamic d)
    {
#if BAD
        F(d);                  // the doc's example
#endif
        dynamic self = this;   // dynamic receiver: checked at run time
        try { self.F(d); }
        catch (RuntimeBinderException e)
        {
            Console.WriteLine(e.Message);
        }
    }
}

class App
{
    static void Main() => new C().M(1);
}
