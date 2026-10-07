// 슬라이드 p15-v14-xm-same — 옛 꼴과 새 꼴이 만드는 정적 메서드, C# 14
using System;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;

static class Ext
{
    public static string Old(this string s, int n) => s.Substring(0, n);

    extension(string s)
    {
        public string New(int n) => s.Substring(0, n);
    }
}

class Program
{
    static void Main()
    {
        foreach (MethodInfo m in typeof(Ext).GetMethods(
            BindingFlags.Public | BindingFlags.Static
            | BindingFlags.DeclaredOnly).OrderBy(m => m.Name))
        {
            string ps = string.Join(", ", m.GetParameters()
                .Select(p => p.ParameterType.Name + " " + p.Name));
            Console.WriteLine("static " + m.ReturnType.Name + " "
                + m.Name
                + "(" + ps + ") [Extension]="
                + m.IsDefined(typeof(ExtensionAttribute)));
        }
        Console.WriteLine("hello".Old(2) + " " + "hello".New(2));
    }
}
