// 슬라이드 p15-v14-sp-list — 다섯 가지 암시적 Span 변환, C# 14
using System;

class Program
{
    static string Show<T>(ReadOnlySpan<T> s) =>
        typeof(T).Name + "[" + s.Length + "]";

    static void Main()
    {
        string[] words = ["a", "b", "c"];
        Span<string> sw = words;            // T[] -> Span
        ReadOnlySpan<string> rw = words;    // T[] -> ROS
        ReadOnlySpan<string> rs = sw;       // Span -> ROS
        ReadOnlySpan<char> rc = "hey";      // string -> ROS<char>
        ReadOnlySpan<object> ra = words;    // T[] -> ROS<base>
        Console.WriteLine(Show(rw) + " " + Show(rs) + " " + Show(rc)
            + " " + Show(ra));
#if COV
        ReadOnlySpan<object> rr = rw;       // ROS -> ROS<base>
        ReadOnlySpan<object> rp = sw;       // Span -> ROS<base>
        Console.WriteLine(Show(rr) + " " + Show(rp));
#endif
    }
}
