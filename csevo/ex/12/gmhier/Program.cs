// 슬라이드 p12-v11-math-inumber — INumber<T> 가 요구하는 것, C# 11.0
using System;
using System.Linq;
using System.Numerics;
using System.Reflection;

class App
{
    const BindingFlags Static = BindingFlags.Static
        | BindingFlags.Public | BindingFlags.NonPublic;

    // Closure of interfaces, and its static abstract / virtual methods
    static void Count(Type t)
    {
        Type[] set = t.GetInterfaces().Append(t).ToArray();
        MethodInfo[] ms = set.SelectMany(i => i.GetMethods(Static))
            .ToArray();
        int ab = ms.Count(m => m.IsAbstract);
        int vi = ms.Count(m => !m.IsAbstract && m.IsVirtual);
        string name = t.Name.Substring(0, t.Name.IndexOf('`'));
        Console.WriteLine(name.PadRight(22) + set.Length.ToString()
            .PadLeft(3) + ab.ToString().PadLeft(5)
            + vi.ToString().PadLeft(5));
    }

    static void Main()
    {
        Console.WriteLine("interface".PadRight(22) + "ifc abst virt");
        Count(typeof(IAdditionOperators<int, int, int>));
        Count(typeof(INumberBase<int>));
        Count(typeof(INumber<int>));
        Count(typeof(IBinaryInteger<int>));
        Count(typeof(IFloatingPointIeee754<double>));
    }
}
