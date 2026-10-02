// 슬라이드 p10-v9-top-ret — return 의 값이 종료 코드, C# 9.0
using System;

if (args.Length == 0)
{
    Console.WriteLine("no input");
    return 2;
}
Console.WriteLine("input: " + args[0]);
#if !BAD
return 0;
#endif
