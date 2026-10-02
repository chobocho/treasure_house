// 슬라이드 p8-v7_2-privprot — private protected, C# 7.2
using System;
using System.Reflection;

class Base
{
    private protected int secret = 7;     // derived AND same assembly
    protected internal int open = 1;      // derived OR same assembly
}

class Derived : Base
{
    public int Peek() => secret;          // derived, same assembly: OK
}

class Other
{
    public int Look(Base b) => b.open;    // same assembly: OK
#if BAD
    public int Try(Base b) => b.secret;   // not derived
#endif
}

class App
{
    static void Main()
    {
        int n = new Derived().Peek() + new Other().Look(new Base());
        Console.WriteLine(n);
        var f = BindingFlags.Instance | BindingFlags.NonPublic
              | BindingFlags.Public;
        foreach (var name in new[] { "secret", "open" })
        {
            var fi = typeof(Base).GetField(name, f);
            Console.WriteLine(name + ": FamANDAssem="
                + fi.IsFamilyAndAssembly
                + " FamORAssem=" + fi.IsFamilyOrAssembly);
        }
    }
}
