// 슬라이드 p3-v2-closure-nest — 블록마다 따로인 클래스, C# 2.0
using System;
using System.Reflection;
using System.Runtime.CompilerServices;

delegate int D();

class App
{
    static bool Generated(Type t)
    {
        return t.IsDefined(typeof(CompilerGeneratedAttribute), false);
    }

    static void Main()
    {
        int y = 100;                     // outer block
        D[] ds = new D[2];
        for (int i = 0; i < 2; i++)
        {
            int z = i * 10;              // inner block, once per pass
            ds[i] = delegate { return y + z; };
        }
        y = 200;
        Console.WriteLine(ds[0]() + " " + ds[1]());

        object o0 = null, o1 = null;
        foreach (FieldInfo f in ds[0].Target.GetType().GetFields())
        {
            if (!Generated(f.FieldType)) continue;
            Console.WriteLine("inner has a field of a generated type");
            o0 = f.GetValue(ds[0].Target);
            o1 = f.GetValue(ds[1].Target);
        }
        Console.WriteLine("inner objects differ: "
            + (ds[0].Target != ds[1].Target));
        Console.WriteLine("they share one outer: " + (o0 == o1));
    }
}
