// 슬라이드 p3-v2-partial-merge — 첫째 조각, C# 2.0
using System;

public sealed partial class Doc : MarshalByRefObject, ICloneable
{
    public object Clone() { return new Doc(); }
}
