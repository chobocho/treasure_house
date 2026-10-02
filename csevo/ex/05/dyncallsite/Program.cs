// 슬라이드 p5-v4-dyn-callsite — 컴파일러가 남긴 호출 지점, C# 4.0
using System;
using System.Reflection;

class Program
{
    static string Pretty(Type t)
    {
        if (!t.IsGenericType) return t.Name;
        string s = t.Name.Substring(0, t.Name.IndexOf('`')) + "<";
        Type[] args = t.GetGenericArguments();
        for (int i = 0; i < args.Length; i++)
        {
            s += (i > 0 ? ", " : "") + Pretty(args[i]);
        }
        return s + ">";
    }

    static void Main()
    {
        dynamic d = "abc";
        Console.WriteLine(d.Length);
        Console.WriteLine(d.ToUpper());

        BindingFlags all = BindingFlags.Public | BindingFlags.NonPublic
                         | BindingFlags.Static | BindingFlags.Instance;
        foreach (Type t in typeof(Program).GetNestedTypes(all))
        {
            Console.WriteLine(t.Name);
            foreach (FieldInfo f in t.GetFields(all))
            {
                Console.WriteLine("  " + f.Name + " : "
                                  + Pretty(f.FieldType));
            }
        }
    }
}
