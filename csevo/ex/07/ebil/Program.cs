// 슬라이드 p7-v6-eb-il — 블록 본문과 같은 멤버가 된다, C# 6.0
using System;
using System.Reflection;

class A
{
    int n = 3;
    public int Block { get { return n * 2; } }
    public int Expr => n * 2;
    public int M1() { return n + 1; }
    public int M2() => n + 1;
}

class Program
{
    static string IL(MethodInfo m)
    {
        byte[] il = m.GetMethodBody().GetILAsByteArray();
        return BitConverter.ToString(il);
    }

    static void Main()
    {
        Type t = typeof(A);
        foreach (string name in new[] { "Block", "Expr" })
        {
            PropertyInfo p = t.GetProperty(name);
            Console.WriteLine(name + ": get=" + p.CanRead
                + " set=" + p.CanWrite + " " + IL(p.GetMethod));
        }
        Console.WriteLine("M1: " + IL(t.GetMethod("M1")));
        Console.WriteLine("M2: " + IL(t.GetMethod("M2")));
        BindingFlags f = BindingFlags.NonPublic | BindingFlags.Instance;
        Console.WriteLine("fields: " + t.GetFields(f).Length);
    }
}
