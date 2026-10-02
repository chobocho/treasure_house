// 슬라이드 p9-v8-dim-prot — protected 인터페이스 멤버, C# 8.0
using System;

interface IBase
{
    protected string Tag() => "base";
    string Show() => "[" + Tag() + "]";
}

interface IFancy : IBase
{
    string IBase.Tag() => "fancy";        // override in an interface
    string Twice() => Tag() + Tag();          // derived interface: ok
}

class Plain : IBase { }
class Fancy : IFancy { }

class App
{
    static void Main()
    {
        Console.WriteLine(((IBase)new Plain()).Show());
        Console.WriteLine(((IBase)new Fancy()).Show());
        Console.WriteLine(((IFancy)new Fancy()).Twice());
#if BAD
        Console.WriteLine(((IBase)new Plain()).Tag());   // outside
#endif
    }
}
