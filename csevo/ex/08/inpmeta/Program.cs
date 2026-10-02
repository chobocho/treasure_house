// 슬라이드 p8-v7_2-in-meta — in 매개변수의 메타데이터, C# 7.2
using System;
using System.Linq;
using System.Reflection;

delegate int D(in int x);

abstract class Shape
{
    public abstract int Virt(in int x);
    public static int Stat(in int x) => x;
}

class App
{
    static void Show(string label, ParameterInfo p)
    {
        var attrs = p.GetCustomAttributes(false)
                     .Select(a => a.GetType().Name);
        var mods = p.GetRequiredCustomModifiers().Select(t => t.Name);
        Console.WriteLine(label + ": " + p.ParameterType.Name
            + " IsIn=" + p.IsIn
            + " attrs=[" + string.Join(",", attrs) + "]"
            + " modreq=[" + string.Join(",", mods) + "]");
    }

    static void Main()
    {
        Show("abstract", typeof(Shape).GetMethod("Virt")
                                      .GetParameters()[0]);
        Show("static  ", typeof(Shape).GetMethod("Stat")
                                      .GetParameters()[0]);
        Show("delegate", typeof(D).GetMethod("Invoke")
                                  .GetParameters()[0]);
    }
}
