// 슬라이드 p2-v1-opnames — 연산자는 op_ 이름의 정적 메서드, C# 1.0
using System;
using System.Reflection;

class Vec
{
    public int X;
    public Vec(int x) { X = x; }
    public static Vec operator +(Vec a, Vec b)
    {
        return new Vec(a.X + b.X);
    }
    public static Vec operator -(Vec a) { return new Vec(-a.X); }
    public static bool operator true(Vec v) { return v.X != 0; }
    public static bool operator false(Vec v) { return v.X == 0; }
    public static implicit operator int(Vec v) { return v.X; }
    public static explicit operator Vec(int x) { return new Vec(x); }
}

class App
{
    static void Main()
    {
        MethodInfo[] ms = typeof(Vec).GetMethods(BindingFlags.Public
            | BindingFlags.Static | BindingFlags.DeclaredOnly);
        string[] names = new string[ms.Length];
        for (int i = 0; i < ms.Length; i++)
        {
            string tag = ms[i].IsSpecialName ? " (special)" : "";
            names[i] = ms[i].Name + tag;
        }
        Array.Sort(names, StringComparer.Ordinal);
        foreach (string n in names) Console.WriteLine(n);
    }
}
