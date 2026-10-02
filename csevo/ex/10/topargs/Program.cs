// 슬라이드 p10-v9-top-args — args 는 최상위 문 안에서만, C# 9.0
using System;

Console.WriteLine("null? " + (args == null) + ", count " + args.Length);
foreach (string a in args)
    Console.WriteLine("  " + a);
#if BAD
static class Util
{
    public static int Count() => args.Length;
}
#endif
