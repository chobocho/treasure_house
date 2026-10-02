// 슬라이드 p10-v9-fnptr-il — calli 와 callvirt, C# 9.0
using System;
using System.Reflection;

unsafe class App
{
    static int Twice(int x) => x * 2;

    static int ViaPointer(int v)
    {
        delegate*<int, int> f = &Twice;
        return f(v);
    }

    static int ViaDelegate(int v)
    {
        Func<int, int> f = Twice;
        return f(v);
    }

    static void Main()
    {
        foreach (string n in new[] { "ViaPointer", "ViaDelegate" })
        {
            MethodInfo m = typeof(App).GetMethod(n,
                BindingFlags.Static | BindingFlags.NonPublic);
            object r = m.Invoke(null, new object[] { 21 });
            Console.WriteLine(n + " = " + r);
            foreach (string op in Il.Ops(m))
                Console.WriteLine("    " + op);
        }
    }
}
