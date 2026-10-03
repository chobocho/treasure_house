// 슬라이드 p12-v11-ck-meta — 메타데이터 이름과 식 트리, C# 11.0
using System;
using System.Linq.Expressions;
using System.Reflection;

readonly struct U8
{
    public readonly byte V;
    public U8(int v) => V = unchecked((byte)v);
    public static U8 operator -(U8 a) => new U8(-a.V);
    public static U8 operator checked -(U8 a) => new U8(checked(-a.V));
    public static U8 operator +(U8 a, U8 b) => new U8(a.V + b.V);
    public static U8 operator checked +(U8 a, U8 b) =>
        new U8(checked((byte)(a.V + b.V)));
    public static explicit operator sbyte(U8 u) =>
        unchecked((sbyte)u.V);
    public static explicit operator checked sbyte(U8 u) =>
        checked((sbyte)u.V);
}

class App
{
    static void Main()
    {
        foreach (MethodInfo m in typeof(U8).GetMethods())
            if (m.IsSpecialName) Console.WriteLine("  " + m.Name);

        Expression<Func<U8, U8, U8>> e1 = (a, b) => checked(a + b);
        Expression<Func<U8, U8, U8>> e2 = (a, b) => a + b;
        foreach (var e in new[] { e1, e2 })
        {
            var be = (BinaryExpression)e.Body;
            Console.WriteLine(be.NodeType + " -> " + be.Method.Name);
        }
    }
}
