// 슬라이드 p15-v14-sp-codegen — 스팬 변환이 부르는 메서드, C# 14
using System;
using System.Linq;

class Program
{
    static int Chars(ReadOnlySpan<char> s) => s.Length;
    static int Items<T>(ReadOnlySpan<T> s) => s.Length;

    static int Str(string s) => Chars(s);         // string -> ROS<char>
    static int Arr(int[] a) => Items<int>(a);     // T[] -> ROS<T>
    static int Spn(Span<int> s) => Items<int>(s); // Span -> ROS
    static bool Has(int[] a) => a.Contains(3);    // which Contains?
    static int Rev(int[] a) => a.Reverse().First();  // which?
#if COV
    static int Up(ReadOnlySpan<string> r) => Items<object>(r);
    static int ArrUp(string[] w) => Items<object>(w);
#endif

    static void Main(string[] args)
    {
        foreach (string m in args) Il.Calls(m);
    }
}
