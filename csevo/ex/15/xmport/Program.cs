// 슬라이드 p15-v14-xm-port — 한 메서드를 새 꼴로 옮겨도 같은 것, C# 14
using System;
using System.Linq;
using System.Reflection;

static class Ext
{
#if NEW
    extension(string s)
    {
        public string Head(int n) => s.Substring(0, n);
    }
#else
    public static string Head(this string s, int n) =>
        s.Substring(0, n);
#endif
}

class Program
{
    static void Main()
    {
        MethodInfo m = typeof(Ext).GetMethod("Head");
        Console.WriteLine(m + " | " + string.Join(", ",
            m.GetParameters().Select(p => p.Name)));
        Console.WriteLine(m.Attributes + " | " + string.Join(", ",
            m.CustomAttributes.Select(a => a.AttributeType.Name)));
        Console.WriteLine("hello".Head(3) + " " + Ext.Head("hello", 4));
    }
}
