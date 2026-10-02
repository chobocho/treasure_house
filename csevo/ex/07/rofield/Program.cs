// 슬라이드 p7-v6-roauto-field — 숨은 필드는 readonly, C# 6.0
using System;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;

class Person
{
    public string A { get; }
    public string B { get; set; }
    public static int C { get; } = 1;
}

class Program
{
    static void Main()
    {
        BindingFlags all = BindingFlags.NonPublic | BindingFlags.Static
            | BindingFlags.Instance;
        FieldInfo[] fs = typeof(Person).GetFields(all)
            .OrderBy(f => f.Name).ToArray();
        foreach (FieldInfo f in fs)
        {
            bool gen = f.IsDefined(typeof(CompilerGeneratedAttribute));
            Console.WriteLine(f.Name + " readonly=" + f.IsInitOnly
                + " static=" + f.IsStatic + " generated=" + gen);
        }
    }
}
