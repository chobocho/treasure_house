// 슬라이드 p10-v9-top-partial — Program 은 partial, C# 9.0
using System;

Console.WriteLine(Helper());
Console.WriteLine(typeof(Program).Name + " " + Version);

#if BAD
class Program
#else
partial class Program
#endif
{
    const int Version = 9;
    static string Helper() => "from my part of Program";
}
