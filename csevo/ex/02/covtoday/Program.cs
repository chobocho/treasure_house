// 슬라이드 p2-v1-covtoday — 배열 공변성은 지금도 그대로, C# 14
using System;
using System.Collections.Generic;

string[] names = ["a", "b"];
object[] objs = names;                    // still allowed, no warning
IEnumerable<object> seq = names;          // C# 4 variance: read only
foreach (var o in seq)
{
    Console.WriteLine(o);
}
objs[0] = 1;                              // still a run-time error
