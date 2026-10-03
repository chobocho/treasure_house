// 슬라이드 p12-v11-shift — 시프트 연산자의 둘째 피연산자, C# 11.0
using System;
using System.Numerics;

readonly struct Big
{
    public readonly ulong V;
    public Big(ulong v) => V = v;
    // The count has the type's own type, not int
    public static Big operator <<(Big b, Big n) =>
        new Big(b.V << (int)n.V);
    public static Big LeadingZeros(Big b) =>
        new Big((ulong)BitOperations.LeadingZeroCount(b.V));
}

class App
{
    static void Main()
    {
        Big x = new Big(0b1011);
        Big norm = x << Big.LeadingZeros(x);     // no cast to int
        Console.WriteLine(Convert.ToString((long)norm.V, 2));
        Console.WriteLine(Big.LeadingZeros(x).V);
    }
}
