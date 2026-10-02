// 슬라이드 p6-v5-caller-bad — 컴파일러가 막는 자리, C# 5.0
using System;
using System.Runtime.CompilerServices;

interface I { void M(string s = ""); }

class C : I
{
    // no default value
    static void A([CallerMemberName] string s) { }
    // int.MaxValue does not fit in a byte
    static void B([CallerLineNumber] byte n = 0) { }
    // a member name is not an int
    static void D([CallerMemberName] int n = 0) { }
    // explicit implementations are never called with omitted args
    void I.M([CallerMemberName] string s) { }
    // two attributes: the line number wins
    static void G([CallerMemberName, CallerLineNumber] object o = null)
    {
        Console.WriteLine(o);
    }
    static void Main() { G(); }
}
