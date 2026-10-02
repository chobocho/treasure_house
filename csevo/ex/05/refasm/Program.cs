// 슬라이드 p5-v4-runtime-ref — dynamic 을 쓰면 참조가 는다, C# 4.0
using System;
using System.Reflection;

class Program
{
    static void Main()
    {
#if DYN
        dynamic d = "dynamic";
        Console.WriteLine(d.Length);
#else
        object o = "static";
        Console.WriteLine(((string)o).Length);
#endif
        Assembly me = typeof(Program).Assembly;
        foreach (AssemblyName r in me.GetReferencedAssemblies())
        {
            Console.WriteLine("references " + r.Name);
        }
    }
}
