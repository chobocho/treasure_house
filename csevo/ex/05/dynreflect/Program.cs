// 슬라이드 p5-v4-dyn-reflection — 리플렉션 대신 dynamic, C# 4.0
using System;
using System.Reflection;
using System.Text;

class Program
{
    static void Main()
    {
        object target = new StringBuilder("C#");

        // reflection: name, types, boxing by hand
        MethodInfo m = target.GetType().GetMethod("Append",
            new Type[] { typeof(int) });
        m.Invoke(target, new object[] { 4 });
        PropertyInfo p = target.GetType().GetProperty("Length");
        Console.WriteLine(target + " " + p.GetValue(target, null));

        // dynamic: the compiler writes the binding request
        dynamic t = target;
        t.Append(".0");
        Console.WriteLine(t + " " + t.Length);
    }
}
