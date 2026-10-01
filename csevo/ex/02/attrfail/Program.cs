// 슬라이드 p2-v1-attrfail — AttributeUsage 가 지키는 것, C# 1.0
using System;

[AttributeUsage(AttributeTargets.Method)]
class AuditAttribute : Attribute { }

[Audit]                                   // only methods allowed
class Store
{
    [Audit]
    [Audit]                               // AllowMultiple is false
    public void Save() { }
}

class App
{
    static void Main() { }
}
