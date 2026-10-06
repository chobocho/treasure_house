// 슬라이드 p13-v12-ce-str — string 은 대상이 아니다(깨지는 변경), C# 12
using System;

class Program
{
    static void Print(char[] arg) { Console.WriteLine("char[]"); }
    static void Print(string arg) { Console.WriteLine("string"); }

    static void Main()
    {
        Print(['a', 'b', 'c']);       // 17.10: no longer ambiguous
        char[] cs = [.. "hey", '!'];  // a string can be spread
        Console.WriteLine(new string(cs));
#if BAD
        string s = ['a', 'b'];
#endif
    }
}
